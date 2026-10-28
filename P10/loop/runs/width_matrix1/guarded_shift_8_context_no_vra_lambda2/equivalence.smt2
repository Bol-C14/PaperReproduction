; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun y () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun c () (_ BitVec 8))
(assert
 (let ((?x37 (bvlshr ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a)))))) ((_ zero_extend 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) y)))))))))
(let ((?x43 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))) ((_ extract 7 0) ?x37))))
(let (($x16 (and (distinct (ite (bvult y (_ bv2 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x14 ((_ extract 7 0) c)))
(let ((?x21 (ite $x16 (bvadd ((_ extract 7 0) (bvlshr ((_ extract 7 0) a) ((_ zero_extend 0) y))) ?x14) b)))
(and (distinct ?x21 (ite $x16 ?x43 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))))))) true)))))))
(check-sat)
