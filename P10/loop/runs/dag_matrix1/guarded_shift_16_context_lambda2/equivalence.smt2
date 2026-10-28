; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 16))
(declare-fun c () (_ BitVec 16))
(declare-fun y () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x29 (bvlshr ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))) ((_ zero_extend 15) ((_ extract 0 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) y))))))))
(let (($x18 (and (distinct (ite (bvult y (_ bv2 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x42 (ite $x18 (bvadd ((_ extract 15 0) ?x29) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) c))))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) b))))))
(let ((?x6 ((_ extract 15 0) c)))
(let ((?x7 (ite $x18 (bvadd ((_ extract 15 0) (bvlshr ((_ extract 15 0) a) ((_ zero_extend 0) y))) ?x6) b)))
(and (distinct ?x7 ?x42) true)))))))
(check-sat)
