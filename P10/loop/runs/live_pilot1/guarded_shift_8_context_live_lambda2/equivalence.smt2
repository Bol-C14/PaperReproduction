; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun c () (_ BitVec 8))
(declare-fun y () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x43 (bvlshr ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))) ((_ zero_extend 7) ((_ extract 0 0) ((_ extract 0 0) ((_ extract 7 0) y)))))))
(let (($x19 (and (distinct (ite (bvult y (_ bv2 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x38 (ite $x19 (bvadd ((_ extract 7 0) ?x43) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))) ((_ extract 7 0) ((_ extract 7 0) b)))))
(let ((?x17 ((_ extract 7 0) c)))
(let ((?x21 (ite $x19 (bvadd ((_ extract 7 0) (bvlshr ((_ extract 7 0) a) ((_ zero_extend 0) y))) ?x17) b)))
(and (distinct ?x21 ?x38) true)))))))
(check-sat)
